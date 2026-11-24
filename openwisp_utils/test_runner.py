"""Validate focused test labels without choosing a test runner."""

from importlib import import_module
from unittest import TestCase


class InvalidTestArgument(ValueError):
    """A test argument is outside the caller's reviewed allowlist."""


def parse_test_arguments(arguments, label_pattern, allowed_flags, require_label=False):
    """Return matched labels and flags, rejecting unsupported arguments."""
    labels = []
    flags = []
    for argument in arguments:
        if argument in allowed_flags:
            flags.append(argument)
            continue
        match = label_pattern.fullmatch(argument)
        if not match:
            raise InvalidTestArgument(f"Unsupported test argument: {argument}")
        labels.append(match)
    if require_label and not labels:
        raise InvalidTestArgument(
            "Unsupported test arguments: a test label is required"
        )
    return labels, flags


def validate_test_classes(labels):
    """Reject class labels that do not identify a unittest TestCase.

    Call this after the caller has initialized any framework needed to
    import its test modules. Labels and test code remain untrusted.
    """
    for match in labels:
        if not match.group("class"):
            continue
        module_name = match.group("module")
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name or module_name.startswith(f"{error.name}."):
                raise InvalidTestArgument(
                    f"Unsupported test argument: {match.group(0)}"
                ) from error
            raise
        candidate = getattr(module, match.group("class"), None)
        if not isinstance(candidate, type) or not issubclass(candidate, TestCase):
            raise InvalidTestArgument(f"Unsupported test argument: {match.group(0)}")
