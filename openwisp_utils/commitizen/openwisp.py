import re

from commitizen.cz.base import BaseCommitizen, ValidationResult

_CUSTOM_PREFIX_RE = re.compile(r"^[a-z0-9!/:-]+$")
_TITLE_ISSUE_RE = re.compile(r"^[A-Z][^\n]* \#(\d+)$")


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
        "chores",
        "qa",
        "deps",
        "release",
        "bump",
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
        if not _TITLE_ISSUE_RE.match(value):
            return (
                "Commit title must start with a capital letter and "
                "end with an issue number (e.g. #104)."
            )
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
        if not match:
            raise ValueError(
                "Commit title must end with an issue reference like #<issue_number>."
            )
        issue_number = match.group(1)
        return f"{prefix} {title}\n\n" f"{body}\n\n" f"Fixes #{issue_number}"

    def validate_commit_message(
        self,
        *,
        commit_msg: str,
        pattern: re.Pattern[str],
        allow_abort: bool,
        allowed_prefixes: list[str],
        max_msg_length: int | None,
        commit_hash: str,
    ) -> ValidationResult:
        """Validate commit message and return user-friendly errors."""
        if not commit_msg:
            return ValidationResult(
                allow_abort, [] if allow_abort else ["commit message is empty"]
            )
        # valid prefixes ok
        if any(map(commit_msg.startswith, allowed_prefixes)):
            return ValidationResult(True, [])
        if pattern.match(commit_msg):
            return ValidationResult(True, [])
        # limit exceeded
        if max_msg_length is not None and max_msg_length > 0:
            msg_len = len(commit_msg.partition("\n")[0].strip())
            if msg_len > max_msg_length:
                return ValidationResult(
                    False,
                    [
                        f"commit message length exceeds the limit ({max_msg_length} chars)",
                    ],
                )
        # Return user-friendly error instead of raw regex
        return ValidationResult(
            False,
            [
                "Invalid commit message.\n\n"
                "Expected format:\n\n"
                "  [prefix] Capitalized title #<issue>\n\n"
                "  <long-description>\n\n"
                "  Fixes #<issue>\n\n"
                "Example:\n\n"
                "  [feature] Add subnet import support #104\n\n"
                "  Add support for importing multiple subnets from a CSV file.\n\n"
                "  Fixes #104"
            ],
        )

    def format_error_message(self, message: str) -> str:
        return (
            "Invalid commit message.\n\n"
            "Expected format:\n\n"
            "  [prefix] Capitalized title #<issue>\n\n"
            "  <long-description>\n\n"
            "  Fixes #<issue>\n\n"
            "Example:\n\n"
            "  [feature] Add subnet import support #104\n\n"
            "  Add support for importing multiple subnets from a CSV file.\n\n"
            "  Fixes #104"
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
        # Allow merge commits (starting with "Merge") or regular commits with prefix
        return r"(?sm)^(?:Merge .*|\[[a-z0-9!/:-]+\] [A-Z][^\n]*( #(?P<issue>\d+))?$(\n\n.+\n\nFixes #(?P=issue)\n?)?)$"  # noqa: E501

    def info(self) -> str:
        prefixes_list = "\n".join(f"  - {prefix}" for prefix in self.ALLOWED_PREFIXES)
        return (
            "OpenWISP Commit Convention\n\n"
            "Commit messages must follow this structure:\n\n"
            "  [type] Capitalized title #<issue_number>\n\n"
            "  <description>\n\n"
            "  Fixes #<issue_number>\n\n"
            f"Allowed commit prefixes:\n\n{prefixes_list}\n\n"
            "If in doubt, use chores."
        )
