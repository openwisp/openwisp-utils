"""Validate focused test labels without choosing a test runner."""

import os
import re
import sys
from importlib import import_module
from inspect import getattr_static, isabstract
from pathlib import Path
from types import FunctionType, ModuleType
from unittest import TestCase, defaultTestLoader


class InvalidTestArgument(ValueError):
    """A test argument is outside the caller's reviewed allowlist."""


def compile_test_label_pattern(
    module_roots=("tests",), exact_modules=(), allow_subpackages=False
):
    """Build a pattern for test modules under trusted roots or exact modules."""
    if isinstance(module_roots, str):
        module_roots = (module_roots,)
    if isinstance(exact_modules, str):
        exact_modules = (exact_modules,)
    module_roots = tuple(module_roots)
    exact_modules = tuple(exact_modules)
    names = (*module_roots, *exact_modules)
    if not names or any(
        not isinstance(name, str)
        or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", name, re.ASCII)
        for name in names
    ):
        raise ValueError("Test module roots must be dotted Python identifiers")
    # A package segment cannot consume a test module and hide a callable.
    subpackages = r"(?:\.(?!test_)[a-z_]\w*)*" if allow_subpackages else ""
    modules = [rf"{re.escape(root)}{subpackages}\.test_\w+" for root in module_roots]
    modules.extend(re.escape(name) for name in exact_modules)
    return re.compile(
        rf"(?P<module>{'|'.join(modules)})"
        r"(?:\.(?P<class>[A-Z]\w*)(?:\.test_\w+)?)?",
        re.ASCII,
    )


DEFAULT_TEST_LABEL_PATTERN = compile_test_label_pattern()
TEST_CLASS_LABEL_PATTERN = re.compile(
    r"(?P<class>Test[A-Za-z0-9_]+)(?:\.test_[A-Za-z0-9_]+)?", re.ASCII
)


def parse_test_arguments(
    arguments,
    label_pattern=DEFAULT_TEST_LABEL_PATTERN,
    allowed_flags=(),
    require_label=False,
):
    """Return matched labels and flags, rejecting unsupported arguments."""
    if isinstance(allowed_flags, str):
        allowed_flags = (allowed_flags,)
    labels = []
    flags = []
    for argument in arguments:
        if argument in allowed_flags:
            flags.append(argument)
            continue
        if argument.startswith("-"):
            raise InvalidTestArgument("Unsupported test argument")
        match = label_pattern.fullmatch(argument)
        if not match:
            raise InvalidTestArgument("Unsupported test argument")
        labels.append(match)
    if require_label and not labels:
        raise InvalidTestArgument(
            "Unsupported test arguments: a test label is required"
        )
    return labels, flags


def validate_test_labels(labels):
    """Require test modules and non-empty unittest TestCase classes.

    Call this after the caller has initialized any framework needed to
    import its test modules. Labels and test code remain untrusted.
    """
    modules = []
    for match in labels:
        module_name = match.group("module")
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name or module_name.startswith(f"{error.name}."):
                raise InvalidTestArgument("Unsupported test argument") from error
            raise
        if not isinstance(module, ModuleType):
            raise InvalidTestArgument("Unsupported test argument")
        modules.append((match, module))
    # Import all selected modules first: a later import can change an earlier one.
    for match, module in modules:
        module_name = match.group("module")
        # unittest traverses package attributes even when the module is cached.
        parts = module_name.split(".")
        for index in range(1, len(parts)):
            parent = sys.modules.get(".".join(parts[:index]))
            child = sys.modules.get(".".join(parts[: index + 1]))
            if (
                parent is None
                or child is None
                or vars(parent).get(parts[index]) is not child
            ):
                raise InvalidTestArgument("Unsupported test argument")
        class_name = match.group("class")
        if not class_name:
            continue
        candidate = getattr(module, class_name, None)
        if (
            not isinstance(candidate, type)
            or not issubclass(candidate, TestCase)
            or isabstract(candidate)
        ):
            raise InvalidTestArgument("Unsupported test argument")
        prefix = f"{module_name}.{class_name}."
        if match.group(0).startswith(prefix):
            method_name = match.group(0).removeprefix(prefix)
            method = getattr_static(candidate, method_name, None)
            if not isinstance(method, FunctionType):
                raise InvalidTestArgument("Unsupported test argument")
        else:
            run_test = getattr_static(candidate, "runTest", None)
            if isinstance(run_test, (classmethod, staticmethod)):
                run_test = run_test.__func__
            if not defaultTestLoader.getTestCaseNames(candidate) and not callable(
                run_test
            ):
                raise InvalidTestArgument("Unsupported test argument")


def compile_test_file_pattern(roots=("tests",), kind="python"):
    """Build a pattern for Python, Lua, or Jest test files under trusted roots."""
    if isinstance(roots, str):
        roots = (roots,)
    roots = tuple(roots)
    if not roots or any(
        not isinstance(root, str)
        or not re.fullmatch(r"\.?[A-Za-z0-9_-]+(?:/\.?[A-Za-z0-9_-]+)*", root)
        for root in roots
    ):
        raise ValueError("Test roots must be relative directory names")
    filenames = {
        "python": r"test_[A-Za-z0-9_]+\.py",
        "lua": r"test_[A-Za-z0-9_]+\.lua",
        "jest": r"[A-Za-z0-9_./-]+\.(?:test|spec)\.jsx?",
    }
    if kind not in filenames:
        raise ValueError(f"Unsupported test file kind: {kind}")
    return re.compile(
        rf"(?:{'|'.join(re.escape(root) for root in roots)})/{filenames[kind]}"
    )


DEFAULT_TEST_FILE_PATTERN = compile_test_file_pattern()


def parse_test_files(
    arguments,
    file_pattern=DEFAULT_TEST_FILE_PATTERN,
    allowed_flags=(),
    root=".",
    max_files=None,
    require_exists=True,
):
    """Validate test files and flags, rejecting missing files and symlinks."""
    matches, flags = parse_test_arguments(arguments, file_pattern, allowed_flags)
    for index, match in enumerate(matches):
        name = match.group(0)
        if (
            (max_files is not None and index >= max_files)
            or ".." in name
            or Path(name).anchor
        ):
            raise InvalidTestArgument("Unsupported test argument")
        path = Path(root)
        for part in Path(name).parts:
            path /= part
            if path.is_symlink():
                raise InvalidTestArgument("Unsupported test argument")
        if require_exists and not path.is_file():
            raise InvalidTestArgument("Unsupported test argument")
    return matches, flags


def prepare_focused_django_tests(
    arguments, label_pattern, sample_modules=(), allowed_flags=()
):
    """Prepare validated focused arguments before Django loads its settings.

    Sample and regular tests need different model configurations, so they
    cannot be mixed. The caller must still initialize Django and validate
    the returned labels before executing the tests.
    """
    if isinstance(sample_modules, str):
        sample_modules = (sample_modules,)
    labels, flags = parse_test_arguments(
        arguments, label_pattern, allowed_flags, require_label=True
    )
    sample_labels = [
        label for label in labels if label.group("module") in sample_modules
    ]
    if sample_labels and len(sample_labels) != len(labels):
        raise InvalidTestArgument(
            "Unsupported test argument: run sample app tests separately"
        )
    if sample_labels:
        os.environ["SAMPLE_APP"] = "1"
    else:
        os.environ.pop("SAMPLE_APP", None)
    sys.argv[1:] = ["test", *(label.group(0) for label in labels), *flags]
    return labels
