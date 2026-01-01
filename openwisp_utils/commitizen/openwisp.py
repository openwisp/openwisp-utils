import re

from commitizen.cz.base import BaseCommitizen

_CUSTOM_PREFIX_RE = re.compile(r"^[a-z0-9!:-]+$")
_TITLE_ISSUE_RE = re.compile(r"#(\d+)$")
_HEADER_RE = re.compile(r"^\[[a-z0-9:!-]+\] [A-Z].*\s#\d+$")
_FIXES_RE = re.compile(r"^Fixes #(\d+)$", re.MULTILINE)


class OpenWispCommitizen(BaseCommitizen):
    """Commitizen plugin for OpenWISP commit conventions."""

    # Single source for allowed prefixes
    ALLOWED_PREFIXES = [
        "feature",
        "change",
        "fix",
        "docs",
        "test",
        "ci",
        "chore",
        "qa",
        "other",
    ]

    def _validate_custom_prefix(self, value: str):
        value = value.strip()
        if not value:
            return "Custom prefix cannot be empty."
        if not _CUSTOM_PREFIX_RE.match(value):
            return "Prefix must be lowercase."
        return True

    def _validate_title(self, value: str) -> bool | str:
        value = value.strip()
        if not value:
            return "Commit title cannot be empty."
        if not value[0].isupper():
            return "Commit title must start with a capital letter."
        if not _TITLE_ISSUE_RE.search(value):
            return "Please add the issue number at the end of the title " "(e.g. #104)."
        return True

    def questions(self):
        return [
            {
                "type": "list",
                "name": "change_type",
                "message": "Select the type of change you are committing",
                "choices": [
                    {"value": prefix, "name": f"[{prefix}]"}
                    for prefix in self.ALLOWED_PREFIXES
                ],
            },
            {
                "type": "input",
                "name": "custom_prefix",
                "message": "Enter custom prefix (without square brackets):",
                "when": lambda answers: answers.get("change_type") == "other",
                "validate": self._validate_custom_prefix,
            },
            {
                "type": "input",
                "name": "title",
                "message": "Commit title (short, first letter capital)",
                "validate": self._validate_title,
            },
            {
                "type": "input",
                "name": "how",
                "message": ("Describe what you changed and how it addresses the issue"),
                "validate": lambda v: (
                    True if v.strip() else "Commit body cannot be empty."
                ),
            },
        ]

    def message(self, answers):
        if answers["change_type"] == "other":
            prefix_value = answers["custom_prefix"]
        else:
            prefix_value = answers["change_type"]

        prefix = f"[{prefix_value}]"
        title = answers["title"].strip()
        body = answers["how"].strip()

        # Extract issue number from title
        match = _TITLE_ISSUE_RE.search(title)
        issue_number = match.group(1)

        return f"{prefix} {title}\n\n" f"{body}\n\n" f"Fixes #{issue_number}"

    def validate_commit_message(self, message: str) -> bool:

        lines = message.splitlines()
        if not lines:
            return False

        # Validate header
        header = lines[0]
        if not _HEADER_RE.match(header):
            return False

        title_issue = _TITLE_ISSUE_RE.search(header)
        if not title_issue:
            return False

        title_issue_num = title_issue.group(1)

        # Remove the Fixes footer before checking body
        body_and_footer = "\n".join(lines[1:]).strip()

        # Remove footer
        body = _FIXES_RE.sub("", body_and_footer).strip()
        if not body:
            return False

        fixes_match = _FIXES_RE.search(message)
        if not fixes_match:
            return False

        fixes_issue_num = fixes_match.group(1)

        # Ensure title and footer reference same issue
        if title_issue_num != fixes_issue_num:
            return False

        return True

    def format_error_message(self, message: str) -> str:
        return (
            "Invalid commit message.\n\n"
            "Expected format:\n\n"
            "[prefix] Title starting with capital letter #<issue>\n\n"
            "<commit body>\n\n"
            "Fixes #<issue>\n\n"
            "Example:\n"
            "[feature] Add subnet import support #104\n\n"
            "Add support for importing multiple subnets from a CSV file.\n\n"
            "Fixes #104"
        )

    def example(self) -> str:
        return (
            "[feature] Add commit convention enforcement #110\n\n"
            "Introduce a Commitizen-based commit workflow to standardize\n"
            "commit messages across the OpenWISP project.\n\n"
            "Fixes #110"
        )

    def schema(self) -> str:
        return "[<type>] <Title>"

    def schema_pattern(self) -> str:
        return r"^\[(feature|change|fix|docs|test|ci|chore|qa)\] [A-Z].+"

    def info(self) -> str:
        return (
            "OpenWISP Commit Convention\n\n"
            "Commit messages must follow this structure:\n\n"
            "[type] Capitalized title #<issue_number>\n\n"
            "<description>\n\n"
            "Fixes #<issue_number>\n\n"
            "Allowed commit types:\n"
            "- feature\n"
            "- change\n"
            "- fix\n"
            "- docs\n"
            "- test\n"
            "- ci\n"
            "- chore\n"
            "- qa\n\n"
            "If none of the predefined types apply, contributors can select\n"
            "the 'other' option and provide a custom type enclosed in square brackets."
        )

    def __init__(self, config):
        super().__init__(config)
