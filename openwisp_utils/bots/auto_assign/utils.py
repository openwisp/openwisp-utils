#!/usr/bin/env python3
"""Shared utility functions for bot modules"""

import re


def extract_linked_issues(pr_body):
    """Extract issue numbers from PR body.

    Returns a list of unique issue numbers referenced in the PR body using
    keywords like 'fixes', 'closes', 'resolves', 'relates to', 'related
    to'. Supports patterns with optional colons and owner/repo references.
    """
    if not pr_body:
        return []
    issue_pattern = r"(?:fix(?:es)?|close[sd]?|resolve[sd]?|relate[sd]?\s+to)\s*:?\s*(?:[\w-]+/[\w-]+)?#(\d+)"
    matches = re.findall(issue_pattern, pr_body, re.IGNORECASE)
    return list(dict.fromkeys(int(match) for match in matches))
