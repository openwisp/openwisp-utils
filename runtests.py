#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, "tests")
os.environ["GITHUB_TOKEN"] = ""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openwisp2.settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    args = sys.argv
    args.insert(1, "test")
    args.insert(2, "test_project")
    args.insert(3, "openwisp_utils.metric_collection")
    execute_from_command_line(args)

    # Check if selenium_tests tag is requested - skip pytest in that case
    skip_pytest = "--tag=selenium_tests" in args
    if skip_pytest:
        sys.exit(0)
    # Run pytest if not skipped
    import pytest

    pytest_exit_code = pytest.main(
        [
            "openwisp_utils/releaser/tests",
        ]
    )
    sys.exit(pytest_exit_code)
