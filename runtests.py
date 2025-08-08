#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

sys.path.insert(0, "tests")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openwisp2.settings")


def run_django_tests():
    from django.core.management import execute_from_command_line

    args = sys.argv
    args.insert(1, "test")
    args.insert(2, "test_project")
    args.insert(3, "openwisp_utils.metric_collection")
    args.insert(4, "test_generate_changelog")

    execute_from_command_line(args)


def run_releaser_tests():
    """Runs the releaser tool tests using pytest."""
    command = [sys.executable, "-m", "pytest", "releaser/tests/"]
    result = subprocess.run(command)

    if result.returncode != 0:
        print(f"Releaser tests failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    print("Releaser tests passed.")


if __name__ == "__main__":
    run_django_tests()
    run_releaser_tests()
