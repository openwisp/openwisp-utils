#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, "tests")
os.environ["GITHUB_TOKEN"] = ""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openwisp2.settings")

if __name__ == "__main__":
    import pytest
    from django.core.management import execute_from_command_line

    args = sys.argv
    args.insert(1, "test")
    args.insert(2, "test_project")
    args.insert(3, "openwisp_utils.metric_collection")
    args.insert(4, "openwisp_utils.bots")
    execute_from_command_line(args)
    sys.exit(pytest.main([os.path.join("openwisp_utils/releaser/tests")]))
